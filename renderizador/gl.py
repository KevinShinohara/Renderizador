#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# pylint: disable=invalid-name

"""
Biblioteca Gráfica / Graphics Library.
 
Desenvolvido por: <Kevin Nagayuki Shinohara>
Disciplina: Computação Gráfica
Data: <DATA DE INÍCIO DA IMPLEMENTAÇÃO>
"""
 
import time         # Para operações com tempo
import gpu          # Simula os recursos de uma GPU
import math         # Funções matemáticas
import numpy as np  # Biblioteca do Numpy
 
class GL:
    """Classe que representa a biblioteca gráfica (Graphics Library)."""
 
    width = 800   # largura da tela
    height = 600  # altura da tela
    near = 0.01   # plano de corte próximo
    far = 1000    # plano de corte distante
    matrizes = {'transform_in': [np.identity(4)], 'viewpoint': np.identity(4), 'perspective': np.identity(4)}
    current_texture = None
    # Buffers para supersampling e Z-buffer
    super_buffer = None
    z_buffer = None
    supersampling_factor = 2  # Fator de supersampling
 
    # Controle de cores por vértice
    colorPerVertex = False
 
    @staticmethod
    def setup(width, height, near=0.01, far=1000):
        """Definr parametros para câmera de razão de aspecto, plano próximo e distante."""
        GL.width = width
        GL.height = height
        GL.near = near
        GL.far = far
 
        # Inicializa o super buffer e o Z-buffer com o fator de supersampling
        GL.super_width = GL.width * GL.supersampling_factor
        GL.super_height = GL.height * GL.supersampling_factor
        GL.super_buffer = np.zeros((GL.super_height, GL.super_width, 3), dtype=np.uint8)
        GL.z_buffer = np.full((GL.super_height, GL.super_width), 1.0)

    def compute_barycentric_coordinates(tri, x, y):
        x1, y1 = tri[0], tri[1]
        x2, y2 = tri[3], tri[4]
        x3, y3 = tri[6], tri[7]
        denominator = ((y2 - y3)*(x1 - x3) + (x3 - x2)*(y1 - y3))
        if denominator == 0:
            return None  # Evitar divisão por zero
        alpha = ((y2 - y3)*(x - x3) + (x3 - x2)*(y - y3)) / denominator
        beta = ((y3 - y1)*(x - x3) + (x1 - x3)*(y - y3)) / denominator
        gamma = 1 - alpha - beta
        return alpha, beta, gamma

 
    @staticmethod
    def downsample():
        """Função para realizar o downsampling do super_buffer para o tamanho da tela."""
 
        factor = GL.supersampling_factor
        for y in range(GL.height):
            for x in range(GL.width):
                # Média das cores do super buffer
                super_y = y * factor
                super_x = x * factor
                region = GL.super_buffer[super_y:super_y + factor, super_x:super_x + factor]
                color = np.mean(region, axis=(0, 1)).astype(np.uint8)
                # Desenha o pixel na tela
                gpu.GPU.draw_pixel([x, y], gpu.GPU.RGB8, color.tolist())
 
    @staticmethod
    def polypoint2D(point, colors):
        """Função usada para renderizar Polypoint2D."""
        # Encontrando a cor
        lista_rgb = [int(round(c * 255)) for c in colors['emissiveColor']]
 
        # Encontrando os pontos
        for i in range(0, len(point), 2):
            pos_x = int(point[i])
            pos_y = int(point[i + 1])
            gpu.GPU.draw_pixel([pos_x, pos_y], gpu.GPU.RGB8, lista_rgb)
 
    @staticmethod
    def polyline2D(lineSegments, colors):
        """Função usada para renderizar Polyline2D."""
        # https://www.web3d.org/specifications/X3Dv4/ISO-IEC19775-1v4-IS/Part01/components/geometry2D.html#Polyline2D
        # Nessa função você receberá os pontos de uma linha no parâmetro lineSegments, esses
        # pontos são uma lista de pontos x, y sempre na ordem. Assim point[0] é o valor da
        # coordenada x do primeiro ponto, point[1] o valor y do primeiro ponto. Já point[2] é
        # a coordenada x do segundo ponto e assim por diante. Assuma a quantidade de pontos
        # pelo tamanho da lista. A quantidade mínima de pontos são 2 (4 valores), porém a
        # função pode receber mais pontos para desenhar vários segmentos. Assuma que sempre
        # vira uma quantidade par de valores.
        # O parâmetro colors é um dicionário com os tipos cores possíveis, para o Polyline2D
        # você pode assumir inicialmente o desenho das linhas com a cor emissiva (emissiveColor).
        # Função auxiliar para desenhar uma linha entre dois pontos (x0, y0) e (x1, y1)
        points_to_draw = []
 
        # Itera pelos pares de pontos na lista lineSegments
        for i in range(0, len(lineSegments) - 2, 2):
            x0 = int(lineSegments[i])
            y0 = int(lineSegments[i + 1])
            x1 = int(lineSegments[i + 2])
            y1 = int(lineSegments[i + 3])
 
            # Diferenças absolutas
            dx = abs(x1 - x0)
            dy = abs(y1 - y0)
 
            # Determina as direções dos incrementos
            sx = 1 if x0 < x1 else -1
            sy = 1 if y0 < y1 else -1
 
            # Inicializa o erro
            err = dx - dy
 
            # Algoritmo de Bresenham para rasterização de linhas
            for _ in range(max(dx, dy) + 1):
                # Adiciona o ponto atual à lista
                points_to_draw.extend([x0, y0])
                if x0 == x1 and y0 == y1:
                    break
                e2 = 2 * err
                if e2 > -dy:
                    err -= dy
                    x0 += sx
                if e2 < dx:
                    err += dx
                    y0 += sy
 
        # Chama a função polypoint2D com os pontos acumulados e as cores
        GL.polypoint2D(points_to_draw, colors)
    @staticmethod
    def circle2D(radius, colors):
        """Função usada para renderizar Circle2D."""
        # https://www.web3d.org/specifications/X3Dv4/ISO-IEC19775-1v4-IS/Part01/components/geometry2D.html#Circle2D
        # Nessa função você receberá um valor de raio e deverá desenhar o contorno de
        # um círculo.
        # O parâmetro colors é um dicionário com os tipos cores possíveis, para o Circle2D
        # você pode assumir o desenho das linhas com a cor emissiva (emissiveColor).
 
        print("Circle2D : radius = {0}".format(radius)) # imprime no terminal
        print("Circle2D : colors = {0}".format(colors)) # imprime no terminal as cores
       
        # Exemplo:
        pos_x = GL.width//2
        pos_y = GL.height//2
        gpu.GPU.draw_pixel([pos_x, pos_y], gpu.GPU.RGB8, [255, 0, 255])  # altera pixel (u, v, tipo, r, g, b)
        # cuidado com as cores, o X3D especifica de (0,1) e o Framebuffer de (0,255)
 
    @staticmethod
    def triangleSet2D(vertices, colors, vertex_colors=None, z_values=None,tex_coords=None):
        """Função usada para renderizar TriangleSet2D."""
        # https://www.web3d.org/specifications/X3Dv4/ISO-IEC19775-1v4-IS/Part01/components/geometry2D.html#TriangleSet2D
        # Nessa função você receberá os vertices de um triângulo no parâmetro vertices,
        # esses pontos são uma lista de pontos x, y sempre na ordem. Assim point[0] é o
        # valor da coordenada x do primeiro ponto, point[1] o valor y do primeiro ponto.
        # Já point[2] é a coordenada x do segundo ponto e assim por diante. Assuma que a
        # quantidade de pontos é sempre multiplo de 3, ou seja, 6 valores ou 12 valores, etc.
        # O parâmetro colors é um dicionário com os tipos cores possíveis, para o TriangleSet2D
        # você pode assumir inicialmente o desenho das linhas com a cor emissiva (emissiveColor).
        # print()

        emissive_color = [int(c * 255) for c in colors.get('emissiveColor', [1, 1, 1])]
        transparency = colors.get('transparency', 0)
        opacity = 1 - transparency

        factor = GL.supersampling_factor

        # Processa cada triângulo
        num_vertices = len(vertices)
        for i in range(0, num_vertices - 5, 6):
            # Extrai vértices do triângulo
            x0, y0 = vertices[i], vertices[i + 1]
            x1, y1 = vertices[i + 2], vertices[i + 3]
            x2, y2 = vertices[i + 4], vertices[i + 5]

            # Coordenadas de textura (se disponíveis)
            if tex_coords:
                u0, v0 = tex_coords[i // 2]
                u1, v1 = tex_coords[(i // 2) + 1]
                u2, v2 = tex_coords[(i // 2) + 2]
            else:
                u0 = v0 = u1 = v1 = u2 = v2 = 0  # Valores padrão

            # Verifica se há cores por vértice suficientes
            if vertex_colors and len(vertex_colors) >= ((i // 6) * 9) + 9:
                idx = (i // 6) * 9
                c0 = [int(c * 255) for c in vertex_colors[idx:idx + 3]]
                c1 = [int(c * 255) for c in vertex_colors[idx + 3:idx + 6]]
                c2 = [int(c * 255) for c in vertex_colors[idx + 6:idx + 9]]
            else:
                c0 = c1 = c2 = emissive_color

            if z_values and len(z_values) >= (i // 6) * 3 + 3:
                z0 = z_values[(i // 6) * 3]
                z1 = z_values[(i // 6) * 3 + 1]
                z2 = z_values[(i // 6) * 3 + 2]
            else:
                z0 = z1 = z2 = 0

            x0_s, y0_s = int(round(x0 * factor)), int(round(y0 * factor))
            x1_s, y1_s = int(round(x1 * factor)), int(round(y1 * factor))
            x2_s, y2_s = int(round(x2 * factor)), int(round(y2 * factor))

            min_x = max(min(x0_s, x1_s, x2_s), 0)
            max_x = min(max(x0_s, x1_s, x2_s), GL.super_width - 1)
            min_y = max(min(y0_s, y1_s, y2_s), 0)
            max_y = min(max(y0_s, y1_s, y2_s), GL.super_height - 1)

            denom = ((y1_s - y2_s)*(x0_s - x2_s) + (x2_s - x1_s)*(y0_s - y2_s))
            if denom == 0:
                continue  # Triângulo degenerado

            # Itera sobre a bounding box
            for y in range(min_y, max_y + 1):
                for x in range(min_x, max_x + 1):

                    w0 = ((y1_s - y2_s)*(x - x2_s) + (x2_s - x1_s)*(y - y2_s)) / denom
                    w1 = ((y2_s - y0_s)*(x - x2_s) + (x0_s - x2_s)*(y - y2_s)) / denom
                    w2 = 1 - w0 - w1

                    # Verifica se o ponto está dentro do triângulo
                    if w0 >= 0 and w1 >= 0 and w2 >= 0:
                        # Interpola Z
                        z = w0 * z0 + w1 * z1 + w2 * z2

                        # Teste do Z-buffer
                        if z < GL.z_buffer[y, x]:
                            GL.z_buffer[y, x] = z

                            # Interpola cor ou textura
                            if tex_coords and GL.current_texture is not None:
                                # Interpola coordenadas de textura
                                u = w0 * u0 + w1 * u1 + w2 * u2
                                v = w0 * v0 + w1 * v1 + w2 * v2

                                # Mapear (u, v) para coordenadas de pixel na textura
                                tex_width = GL.current_texture.shape[1]
                                tex_height = GL.current_texture.shape[0]
                                tex_x = int((v) * (tex_width - 1))
                                tex_y = int((1-u)  * (tex_height - 1))

                                # Garantir que as coordenadas estejam dentro dos limites
                                tex_x = np.clip(tex_x, 0, tex_width - 1)
                                tex_y = np.clip(tex_y, 0, tex_height - 1)

                                # Obter a cor do pixel da textura
                                color = GL.current_texture[tex_y, tex_x][:3]
                            else:
                                # Interpola cor
                                r = w0 * c0[0] + w1 * c1[0] + w2 * c2[0]
                                g = w0 * c0[1] + w1 * c1[1] + w2 * c2[1]
                                b = w0 * c0[2] + w1 * c1[2] + w2 * c2[2]
                                color = [int(r), int(g), int(b)]

                            existing_color = GL.super_buffer[y, x]
                            blended_color = [
                                int(opacity * color[0] + transparency * existing_color[0]),
                                int(opacity * color[1] + transparency * existing_color[1]),
                                int(opacity * color[2] + transparency * existing_color[2]),
                            ]

                            GL.super_buffer[y, x] = blended_color


        GL.downsample()
    
    @staticmethod
    def transform_point(point):
        """Aplica transformações a um ponto."""
        ponto_homogeneo = np.array([point[0], point[1], point[2], 1])
        # Aplica transformações
        matriz_modelo = GL.matrizes['transform_in'][-1]
        ponto_transformado = matriz_modelo @ ponto_homogeneo
        ponto_camera = GL.matrizes['viewpoint'] @ ponto_transformado
        ponto_perspectiva = GL.matrizes['perspective'] @ ponto_camera
        ponto_normalizado = ponto_perspectiva / ponto_perspectiva[3]
        # Converte para coordenadas de tela
        x_ndc = ponto_normalizado[0]
        y_ndc = ponto_normalizado[1]
        z_ndc = ponto_normalizado[2]
        x_tela = (x_ndc + 1) * GL.width * 0.5
        y_tela = (1 - y_ndc) * GL.height * 0.5
        z_depth = (z_ndc + 1) * 0.5  

        # print(f"Vértice original: {point}")
        # print(f"Vértice transformado: x={x_tela}, y={y_tela}, z={z_depth}")

        return [x_tela, y_tela, z_depth]
 
    @staticmethod
    def triangleSet(point, colors, vertex_colors=None):
        """Função usada para renderizar TriangleSet."""
        # https://www.web3d.org/specifications/X3Dv4/ISO-IEC19775-1v4-IS/Part01/components/rendering.html#TriangleSet
        # Nessa função você receberá pontos no parâmetro point, esses pontos são uma lista
        # de pontos x, y, e z sempre na ordem. Assim point[0] é o valor da coordenada x do
        # primeiro ponto, point[1] o valor y do primeiro ponto, point[2] o valor z da
        # coordenada z do primeiro ponto. Já point[3] é a coordenada x do segundo ponto e
        # assim por diante.
        # No TriangleSet os triângulos são informados individualmente, assim os três
        # primeiros pontos definem um triângulo, os três próximos pontos definem um novo
        # triângulo, e assim por diante.
        # O parâmetro colors é um dicionário com os tipos cores possíveis, você pode assumir
        # inicialmente, para o TriangleSet, o desenho das linhas com a cor emissiva
        # (emissiveColor), conforme implementar novos materias você deverá suportar outros
        # tipos de cores.
 
        # O print abaixo é só para vocês verificarem o funcionamento, DEVE SER REMOVIDO.
        #print("TriangleSet : pontos = {0}".format(point)) # imprime no terminal pontos
        #print("TriangleSet : colors = {0}".format(colors)) # imprime no terminal as cores
 
        # Exemplo de desenho de um pixel branco na coordenada 10, 10
        #gpu.GPU.draw_pixel([10, 10], gpu.GPU.RGB8, [255, 255, 255])  # altera pixel
 
        vertices = []
        z_values = []
 
        # Aplica transformações em cada ponto
        for i in range(0, len(point), 3):
            transformed = GL.transform_point(point[i:i + 3])
            vertices.extend([transformed[0], transformed[1]])
            z_values.append(transformed[2])
        # print(f"Vértices dos triângulos (2D): {vertices}")
        # print(f"Valores de profundidade (Z): {z_values}")

        GL.triangleSet2D(vertices, colors, vertex_colors, z_values)
 
    @staticmethod
    def viewpoint(position, orientation, fieldOfView):
        """Função usada para renderizar (na verdade coletar os dados) de Viewpoint."""
        # Na função de viewpoint você receberá a posição, orientação e campo de visão da
        # câmera virtual. Use esses dados para poder calcular e criar a matriz de projeção
        # perspectiva para poder aplicar nos pontos dos objetos geométricos.
 
        # O print abaixo é só para vocês verificarem o funcionamento, DEVE SER REMOVIDO.
        # Matrizes de translação e rotação invertidas para a câmera
        matriz_translacao_inversa = np.array([
            [1, 0, 0, -position[0]],
            [0, 1, 0, -position[1]],
            [0, 0, 1, -position[2]],
            [0, 0, 0, 1]
        ])
 
        # Calcular rotação usando quaternion
        angulo = orientation[3]
        eixo = np.array([orientation[0], orientation[1], orientation[2]])
        eixo = eixo / np.linalg.norm(eixo)
        cos_ang = np.cos(angulo)
        sin_ang = np.sin(angulo)
        ux, uy, uz = eixo
 
        matriz_rotacao_inversa = np.array([
            [cos_ang + ux ** 2 * (1 - cos_ang), ux * uy * (1 - cos_ang) - uz * sin_ang, ux * uz * (1 - cos_ang) + uy * sin_ang, 0],
            [uy * ux * (1 - cos_ang) + uz * sin_ang, cos_ang + uy ** 2 * (1 - cos_ang), uy * uz * (1 - cos_ang) - ux * sin_ang, 0],
            [uz * ux * (1 - cos_ang) - uy * sin_ang, uz * uy * (1 - cos_ang) + ux * sin_ang, cos_ang + uz ** 2 * (1 - cos_ang), 0],
            [0, 0, 0, 1]
        ])
 
        # Matriz de visualização
        GL.matrizes['viewpoint'] = matriz_rotacao_inversa @ matriz_translacao_inversa
 
        # Matriz de projeção perspectiva
        aspect = GL.width / GL.height
        fovy = fieldOfView
        f = 1 / math.tan(fovy / 2)
        near = GL.near
        far = GL.far
 
        GL.matrizes['perspective'] = np.array([
            [f / aspect, 0, 0, 0],
            [0, f, 0, 0],
            [0, 0, (far + near) / (near - far), (2 * far * near) / (near - far)],
            [0, 0, -1, 0]
        ])
 
    @staticmethod
    def transform_in(translation, scale, rotation):
        """Função usada para renderizar (na verdade coletar os dados) de Transform."""
        # A função transform_in será chamada quando se entrar em um nó X3D do tipo Transform
        # do grafo de cena. Os valores passados são a escala em um vetor [x, y, z]
        # indicando a escala em cada direção, a translação [x, y, z] nas respectivas
        # coordenadas e finalmente a rotação por [x, y, z, t] sendo definida pela rotação
        # do objeto ao redor do eixo x, y, z por t radianos, seguindo a regra da mão direita.
        # Quando se entrar em um nó transform se deverá salvar a matriz de transformação dos
        # modelos do mundo para depois potencialmente usar em outras chamadas.
        # Quando começar a usar Transforms dentre de outros Transforms, mais a frente no curso
        # Você precisará usar alguma estrutura de dados pilha para organizar as matrizes.
 
        # O print abaixo é só para vocês verificarem o funcionamento, DEVE SER REMOVIDO.
        # Matrizes de translação e escala
        matriz_translacao = np.array([
            [1, 0, 0, translation[0]],
            [0, 1, 0, translation[1]],
            [0, 0, 1, translation[2]],
            [0, 0, 0, 1]
        ])
 
        matriz_escala = np.array([
            [scale[0], 0, 0, 0],
            [0, scale[1], 0, 0],
            [0, 0, scale[2], 0],
            [0, 0, 0, 1]
        ])
 
        angulo = rotation[3]
        eixo = np.array([rotation[0], rotation[1], rotation[2]])
        eixo = eixo / np.linalg.norm(eixo)
        cos_ang = np.cos(angulo)
        sin_ang = np.sin(angulo)
        ux, uy, uz = eixo
 
        matriz_rotacao = np.array([
            [cos_ang + ux ** 2 * (1 - cos_ang), ux * uy * (1 - cos_ang) - uz * sin_ang, ux * uz * (1 - cos_ang) + uy * sin_ang, 0],
            [uy * ux * (1 - cos_ang) + uz * sin_ang, cos_ang + uy ** 2 * (1 - cos_ang), uy * uz * (1 - cos_ang) - ux * sin_ang, 0],
            [uz * ux * (1 - cos_ang) - uy * sin_ang, uz * uy * (1 - cos_ang) + ux * sin_ang, cos_ang + uz ** 2 * (1 - cos_ang), 0],
            [0, 0, 0, 1]
        ])
 
        # Matriz de transformação completa
        matriz_transformacao = matriz_translacao @ matriz_rotacao @ matriz_escala
        matriz_total = GL.matrizes['transform_in'][-1] @ matriz_transformacao
        GL.matrizes['transform_in'].append(matriz_total)
 
    @staticmethod
    def transform_out():
        """Função usada para renderizar (na verdade coletar os dados) de Transform."""
        # A função transform_out será chamada quando se sair em um nó X3D do tipo Transform do
        # grafo de cena. Não são passados valores, porém quando se sai de um nó transform se
        # deverá recuperar a matriz de transformação dos modelos do mundo da estrutura de
        # pilha implementada.
 
        # O print abaixo é só para vocês verificarem o funcionamento, DEVE SER REMOVIDO.
       
        GL.matrizes['transform_in'].pop()
 
    @staticmethod
    def triangleStripSet(point, stripCount, colors, vertex_colors=None):
        """Função usada para renderizar TriangleStripSet."""
        # https://www.web3d.org/specifications/X3Dv4/ISO-IEC19775-1v4-IS/Part01/components/rendering.html#TriangleStripSet
        # A função triangleStripSet é usada para desenhar tiras de triângulos interconectados,
        # você receberá as coordenadas dos pontos no parâmetro point, esses pontos são uma
        # lista de pontos x, y, e z sempre na ordem. Assim point[0] é o valor da coordenada x
        # do primeiro ponto, point[1] o valor y do primeiro ponto, point[2] o valor z da
        # coordenada z do primeiro ponto. Já point[3] é a coordenada x do segundo ponto e assim
        # por diante. No TriangleStripSet a quantidade de vértices a serem usados é informado
        # em uma lista chamada stripCount (perceba que é uma lista). Ligue os vértices na ordem,
        # primeiro triângulo será com os vértices 0, 1 e 2, depois serão os vértices 1, 2 e 3,
        # depois 2, 3 e 4, e assim por diante. Cuidado com a orientação dos vértices, ou seja,
        # todos no sentido horário ou todos no sentido anti-horário, conforme especificado.
 
        current_index = 0
        for strip in stripCount:
            for t in range(strip - 2):
                idxs = []
                if t % 2 == 0:
                    idxs = [current_index + t, current_index + t + 1, current_index + t + 2]
                else:
                    idxs = [current_index + t + 1, current_index + t, current_index + t + 2]
 
                triangle_vertices = []
                z_values = []
                for idx in idxs:
                    v = point[idx * 3: idx * 3 + 3]
                    transformed = GL.transform_point(v)
                    triangle_vertices.extend([transformed[0], transformed[1]])
                    z_values.append(transformed[2])
 
                # Passa cores por vértice se disponíveis
                if vertex_colors:
                    vc = vertex_colors[idx * 3: idx * 3 + 9]
                else:
                    vc = None
 
                GL.triangleSet2D(triangle_vertices, colors, vc, z_values)
 
            current_index += strip
 
    @staticmethod
    def indexedTriangleStripSet(point, index, colors, vertex_colors=None, colorIndex=None):
        """Função usada para renderizar IndexedTriangleStripSet."""
        # https://www.web3d.org/specifications/X3Dv4/ISO-IEC19775-1v4-IS/Part01/components/rendering.html#IndexedTriangleStripSet
        # A função indexedTriangleStripSet é usada para desenhar tiras de triângulos
        # interconectados, você receberá as coordenadas dos pontos no parâmetro point, esses
        # pontos são uma lista de pontos x, y, e z sempre na ordem. Assim point[0] é o valor
        # da coordenada x do primeiro ponto, point[1] o valor y do primeiro ponto, point[2]
        # o valor z da coordenada z do primeiro ponto. Já point[3] é a coordenada x do
        # segundo ponto e assim por diante. No IndexedTriangleStripSet uma lista informando
        # como conectar os vértices é informada em index, o valor -1 indica que a lista
        # acabou. A ordem de conexão será de 3 em 3 pulando um índice. Por exemplo: o
        # primeiro triângulo será com os vértices 0, 1 e 2, depois serão os vértices 1, 2 e 3,
        # depois 2, 3 e 4, e assim por diante. Cuidado com a orientação dos vértices, ou seja,
        # todos no sentido horário ou todos no sentido anti-horário, conforme especificado.
 
        # O print abaixo é só para vocês verificarem o funcionamento, DEVE SER REMOVIDO.
       
        GL.colorPerVertex = True if vertex_colors else False
 
        i = 0
        while i < len(index):
            strip_indices = []
            while i < len(index) and index[i] != -1:
                strip_indices.append(index[i])
                i += 1
            i += 1  # Pula o -1
 
            # Gera triângulos a partir da strip
            for j in range(len(strip_indices) - 2):
                idxs = []
                if j % 2 == 0:
                    idxs = [strip_indices[j], strip_indices[j + 1], strip_indices[j + 2]]
                else:
                    idxs = [strip_indices[j + 1], strip_indices[j], strip_indices[j + 2]]
 
                triangle_vertices = []
                z_values = []
                vertex_colors_list = []
                for idx in idxs:
                    v = point[idx * 3: idx * 3 + 3]
                    transformed = GL.transform_point(v)
                    triangle_vertices.extend([transformed[0], transformed[1]])
                    z_values.append(transformed[2])
 
                    if vertex_colors:
                        if colorIndex:
                            color_idx = colorIndex[idx] * 3
                        else:
                            color_idx = idx * 3
                        vc = vertex_colors[color_idx: color_idx + 3]
                        vertex_colors_list.extend(vc)
 
                if GL.colorPerVertex:
                    GL.triangleSet2D(triangle_vertices, colors, vertex_colors_list, z_values)
                else:
                    GL.triangleSet2D(triangle_vertices, colors, None, z_values)
 
    @staticmethod
    def indexedFaceSet(coord, coordIndex, colorPerVertex, color, colorIndex,
                       texCoord, texCoordIndex, colors, current_texture):
        """Função usada para renderizar IndexedFaceSet."""
        # https://www.web3d.org/specifications/X3Dv4/ISO-IEC19775-1v4-IS/Part01/components/geometry3D.html#IndexedFaceSet
        # A função indexedFaceSet é usada para desenhar malhas de triângulos. Ela funciona de
        # forma muito simular a IndexedTriangleStripSet porém com mais recursos.
        # Você receberá as coordenadas dos pontos no parâmetro cord, esses
        # pontos são uma lista de pontos x, y, e z sempre na ordem. Assim coord[0] é o valor
        # da coordenada x do primeiro ponto, coord[1] o valor y do primeiro ponto, coord[2]
        # o valor z da coordenada z do primeiro ponto. Já coord[3] é a coordenada x do
        # segundo ponto e assim por diante. No IndexedFaceSet uma lista de vértices é informada
        # em coordIndex, o valor -1 indica que a lista acabou.
        # A ordem de conexão não possui uma ordem oficial, mas em geral se o primeiro ponto com os dois
        # seguintes e depois este mesmo primeiro ponto com o terçeiro e quarto ponto. Por exemplo: numa
        # sequencia 0, 1, 2, 3, 4, -1 o primeiro triângulo será com os vértices 0, 1 e 2, depois serão
        # os vértices 0, 2 e 3, e depois 0, 3 e 4, e assim por diante, até chegar no final da lista.
        # Adicionalmente essa implementação do IndexedFace aceita cores por vértices, assim
        # se a flag colorPerVertex estiver habilitada, os vértices também possuirão cores
        # que servem para definir a cor interna dos poligonos, para isso faça um cálculo
        # baricêntrico de que cor deverá ter aquela posição. Da mesma forma se pode definir uma
        # textura para o poligono, para isso, use as coordenadas de textura e depois aplique a
        # cor da textura conforme a posição do mapeamento. Dentro da classe GPU já está
        # implementadado um método para a leitura de imagens.
 
        # Os prints abaixo são só para vocês verificarem o funcionamento, DEVE SER REMOVIDO.
 
        if current_texture:
            GL.current_texture = gpu.GPU.load_texture(current_texture[0])
            GL.current_texture = np.flipud(GL.current_texture)

        GL.colorPerVertex = colorPerVertex
        vertex_colors = color if colorPerVertex and color is not None else None

        i = 0
        while i < len(coordIndex):
            face_indices = []
            tex_indices = []
            while i < len(coordIndex) and coordIndex[i] != -1:
                face_indices.append(coordIndex[i])
                if texCoordIndex:
                    tex_indices.append(texCoordIndex[i])
                i += 1
            i += 1 

            for j in range(1, len(face_indices) - 1):
                idxs = [face_indices[0], face_indices[j + 1], face_indices[j]]

                tex_idxs = [face_indices[0], face_indices[j + 1], face_indices[j]] if tex_indices else None

                triangle_vertices = []
                z_values = []
                vertex_colors_list = []
                tex_coords_list = []
                for idx, tex_idx in zip(idxs, tex_idxs) if tex_indices else zip(idxs, [None]*3):
                    v = coord[idx * 3: idx * 3 + 3]
                    transformed = GL.transform_point(v)
                    triangle_vertices.extend([transformed[0], transformed[1]])
                    z_values.append(transformed[2])

                    if GL.colorPerVertex and vertex_colors is not None:
                        if colorIndex and len(colorIndex) > idx:
                            color_idx = colorIndex[idx] * 3
                        else:
                            color_idx = idx * 3
                        vc = vertex_colors[color_idx: color_idx + 3]
                        vertex_colors_list.extend(vc)
                    else:
                        vertex_colors_list = None

                    if texCoord and texCoordIndex and tex_idx is not None:
                        u = texCoord[tex_idx * 2]
                        v = texCoord[tex_idx * 2 + 1]
                        v = 1 - v 
                        tex_coords_list.append((u, v))
                    else:
                        tex_coords_list = None

                GL.triangleSet2D(triangle_vertices, colors, vertex_colors_list, z_values, tex_coords_list)
                
 
    @staticmethod
    def box(size, colors):
        """Função usada para renderizar Boxes."""
        # https://www.web3d.org/specifications/X3Dv4/ISO-IEC19775-1v4-IS/Part01/components/geometry3D.html#Box
        # A função box é usada para desenhar paralelepípedos na cena. O Box é centrada no
        # (0, 0, 0) no sistema de coordenadas local e alinhado com os eixos de coordenadas
        # locais. O argumento size especifica as extensões da caixa ao longo dos eixos X, Y
        # e Z, respectivamente, e cada valor do tamanho deve ser maior que zero. Para desenha
        # essa caixa você vai provavelmente querer tesselar ela em triângulos, para isso
        # encontre os vértices e defina os triângulos.

        # O print abaixo é só para vocês verificarem o funcionamento, DEVE SER REMOVIDO.
        print("Box : size = {0}".format(size)) # imprime no terminal pontos
        print("Box : colors = {0}".format(colors)) # imprime no terminal as cores

        # Exemplo de desenho de um pixel branco na coordenada 10, 10
        gpu.GPU.draw_pixel([10, 10], gpu.GPU.RGB8, [255, 255, 255])  # altera pixel

    @staticmethod
    def sphere(radius, colors):
        """Função usada para renderizar Esferas."""
        # https://www.web3d.org/specifications/X3Dv4/ISO-IEC19775-1v4-IS/Part01/components/geometry3D.html#Sphere
        # A função sphere é usada para desenhar esferas na cena. O esfera é centrada no
        # (0, 0, 0) no sistema de coordenadas local. O argumento radius especifica o
        # raio da esfera que está sendo criada. Para desenha essa esfera você vai
        # precisar tesselar ela em triângulos, para isso encontre os vértices e defina
        # os triângulos.

        # O print abaixo é só para vocês verificarem o funcionamento, DEVE SER REMOVIDO.
        print("Sphere : radius = {0}".format(radius)) # imprime no terminal o raio da esfera
        print("Sphere : colors = {0}".format(colors)) # imprime no terminal as cores

    @staticmethod
    def cone(bottomRadius, height, colors):
        """Função usada para renderizar Cones."""
        # https://www.web3d.org/specifications/X3Dv4/ISO-IEC19775-1v4-IS/Part01/components/geometry3D.html#Cone
        # A função cone é usada para desenhar cones na cena. O cone é centrado no
        # (0, 0, 0) no sistema de coordenadas local. O argumento bottomRadius especifica o
        # raio da base do cone e o argumento height especifica a altura do cone.
        # O cone é alinhado com o eixo Y local. O cone é fechado por padrão na base.
        # Para desenha esse cone você vai precisar tesselar ele em triângulos, para isso
        # encontre os vértices e defina os triângulos.

        # O print abaixo é só para vocês verificarem o funcionamento, DEVE SER REMOVIDO.
        print("Cone : bottomRadius = {0}".format(bottomRadius)) # imprime no terminal o raio da base do cone
        print("Cone : height = {0}".format(height)) # imprime no terminal a altura do cone
        print("Cone : colors = {0}".format(colors)) # imprime no terminal as cores

    @staticmethod
    def cylinder(radius, height, colors):
        """Função usada para renderizar Cilindros."""
        # https://www.web3d.org/specifications/X3Dv4/ISO-IEC19775-1v4-IS/Part01/components/geometry3D.html#Cylinder
        # A função cylinder é usada para desenhar cilindros na cena. O cilindro é centrado no
        # (0, 0, 0) no sistema de coordenadas local. O argumento radius especifica o
        # raio da base do cilindro e o argumento height especifica a altura do cilindro.
        # O cilindro é alinhado com o eixo Y local. O cilindro é fechado por padrão em ambas as extremidades.
        # Para desenha esse cilindro você vai precisar tesselar ele em triângulos, para isso
        # encontre os vértices e defina os triângulos.

        # O print abaixo é só para vocês verificarem o funcionamento, DEVE SER REMOVIDO.
        print("Cylinder : radius = {0}".format(radius)) # imprime no terminal o raio do cilindro
        print("Cylinder : height = {0}".format(height)) # imprime no terminal a altura do cilindro
        print("Cylinder : colors = {0}".format(colors)) # imprime no terminal as cores

    @staticmethod
    def navigationInfo(headlight):
        """Características físicas do avatar do visualizador e do modelo de visualização."""
        # https://www.web3d.org/specifications/X3Dv4/ISO-IEC19775-1v4-IS/Part01/components/navigation.html#NavigationInfo
        # O campo do headlight especifica se um navegador deve acender um luz direcional que
        # sempre aponta na direção que o usuário está olhando. Definir este campo como TRUE
        # faz com que o visualizador forneça sempre uma luz do ponto de vista do usuário.
        # A luz headlight deve ser direcional, ter intensidade = 1, cor = (1 1 1),
        # ambientIntensity = 0,0 e direção = (0 0 −1).

        # O print abaixo é só para vocês verificarem o funcionamento, DEVE SER REMOVIDO.
        print("NavigationInfo : headlight = {0}".format(headlight)) # imprime no terminal

    @staticmethod
    def directionalLight(ambientIntensity, color, intensity, direction):
        """Luz direcional ou paralela."""
        # https://www.web3d.org/specifications/X3Dv4/ISO-IEC19775-1v4-IS/Part01/components/lighting.html#DirectionalLight
        # Define uma fonte de luz direcional que ilumina ao longo de raios paralelos
        # em um determinado vetor tridimensional. Possui os campos básicos ambientIntensity,
        # cor, intensidade. O campo de direção especifica o vetor de direção da iluminação
        # que emana da fonte de luz no sistema de coordenadas local. A luz é emitida ao
        # longo de raios paralelos de uma distância infinita.

        # O print abaixo é só para vocês verificarem o funcionamento, DEVE SER REMOVIDO.
        print("DirectionalLight : ambientIntensity = {0}".format(ambientIntensity))
        print("DirectionalLight : color = {0}".format(color)) # imprime no terminal
        print("DirectionalLight : intensity = {0}".format(intensity)) # imprime no terminal
        print("DirectionalLight : direction = {0}".format(direction)) # imprime no terminal

    @staticmethod
    def pointLight(ambientIntensity, color, intensity, location):
        """Luz pontual."""
        # https://www.web3d.org/specifications/X3Dv4/ISO-IEC19775-1v4-IS/Part01/components/lighting.html#PointLight
        # Fonte de luz pontual em um local 3D no sistema de coordenadas local. Uma fonte
        # de luz pontual emite luz igualmente em todas as direções; ou seja, é omnidirecional.
        # Possui os campos básicos ambientIntensity, cor, intensidade. Um nó PointLight ilumina
        # a geometria em um raio de sua localização. O campo do raio deve ser maior ou igual a
        # zero. A iluminação do nó PointLight diminui com a distância especificada.

        # O print abaixo é só para vocês verificarem o funcionamento, DEVE SER REMOVIDO.
        print("PointLight : ambientIntensity = {0}".format(ambientIntensity))
        print("PointLight : color = {0}".format(color)) # imprime no terminal
        print("PointLight : intensity = {0}".format(intensity)) # imprime no terminal
        print("PointLight : location = {0}".format(location)) # imprime no terminal

    @staticmethod
    def fog(visibilityRange, color):
        """Névoa."""
        # https://www.web3d.org/specifications/X3Dv4/ISO-IEC19775-1v4-IS/Part01/components/environmentalEffects.html#Fog
        # O nó Fog fornece uma maneira de simular efeitos atmosféricos combinando objetos
        # com a cor especificada pelo campo de cores com base nas distâncias dos
        # vários objetos ao visualizador. A visibilidadeRange especifica a distância no
        # sistema de coordenadas local na qual os objetos são totalmente obscurecidos
        # pela névoa. Os objetos localizados fora de visibilityRange do visualizador são
        # desenhados com uma cor de cor constante. Objetos muito próximos do visualizador
        # são muito pouco misturados com a cor do nevoeiro.

        # O print abaixo é só para vocês verificarem o funcionamento, DEVE SER REMOVIDO.
        print("Fog : color = {0}".format(color)) # imprime no terminal
        print("Fog : visibilityRange = {0}".format(visibilityRange))

    @staticmethod
    def timeSensor(cycleInterval, loop):
        """Gera eventos conforme o tempo passa."""
        # https://www.web3d.org/specifications/X3Dv4/ISO-IEC19775-1v4-IS/Part01/components/time.html#TimeSensor
        # Os nós TimeSensor podem ser usados para muitas finalidades, incluindo:
        # Condução de simulações e animações contínuas; Controlar atividades periódicas;
        # iniciar eventos de ocorrência única, como um despertador;
        # Se, no final de um ciclo, o valor do loop for FALSE, a execução é encerrada.
        # Por outro lado, se o loop for TRUE no final de um ciclo, um nó dependente do
        # tempo continua a execução no próximo ciclo. O ciclo de um nó TimeSensor dura
        # cycleInterval segundos. O valor de cycleInterval deve ser maior que zero.

        # Deve retornar a fração de tempo passada em fraction_changed

        # O print abaixo é só para vocês verificarem o funcionamento, DEVE SER REMOVIDO.
        print("TimeSensor : cycleInterval = {0}".format(cycleInterval)) # imprime no terminal
        print("TimeSensor : loop = {0}".format(loop))

        # Esse método já está implementado para os alunos como exemplo
        epoch = time.time()  # time in seconds since the epoch as a floating point number.
        fraction_changed = (epoch % cycleInterval) / cycleInterval

        return fraction_changed

    @staticmethod
    def splinePositionInterpolator(set_fraction, key, keyValue, closed):
        """Interpola não linearmente entre uma lista de vetores 3D."""
        # https://www.web3d.org/specifications/X3Dv4/ISO-IEC19775-1v4-IS/Part01/components/interpolators.html#SplinePositionInterpolator
        # Interpola não linearmente entre uma lista de vetores 3D. O campo keyValue possui
        # uma lista com os valores a serem interpolados, key possui uma lista respectiva de chaves
        # dos valores em keyValue, a fração a ser interpolada vem de set_fraction que varia de
        # zeroa a um. O campo keyValue deve conter exatamente tantos vetores 3D quanto os
        # quadros-chave no key. O campo closed especifica se o interpolador deve tratar a malha
        # como fechada, com uma transições da última chave para a primeira chave. Se os keyValues
        # na primeira e na última chave não forem idênticos, o campo closed será ignorado.

        # O print abaixo é só para vocês verificarem o funcionamento, DEVE SER REMOVIDO.
        print("SplinePositionInterpolator : set_fraction = {0}".format(set_fraction))
        print("SplinePositionInterpolator : key = {0}".format(key)) # imprime no terminal
        print("SplinePositionInterpolator : keyValue = {0}".format(keyValue))
        print("SplinePositionInterpolator : closed = {0}".format(closed))

        # Abaixo está só um exemplo de como os dados podem ser calculados e transferidos
        value_changed = [0.0, 0.0, 0.0]
        
        return value_changed

    @staticmethod
    def orientationInterpolator(set_fraction, key, keyValue):
        """Interpola entre uma lista de valores de rotação especificos."""
        # https://www.web3d.org/specifications/X3Dv4/ISO-IEC19775-1v4-IS/Part01/components/interpolators.html#OrientationInterpolator
        # Interpola rotações são absolutas no espaço do objeto e, portanto, não são cumulativas.
        # Uma orientação representa a posição final de um objeto após a aplicação de uma rotação.
        # Um OrientationInterpolator interpola entre duas orientações calculando o caminho mais
        # curto na esfera unitária entre as duas orientações. A interpolação é linear em
        # comprimento de arco ao longo deste caminho. Os resultados são indefinidos se as duas
        # orientações forem diagonalmente opostas. O campo keyValue possui uma lista com os
        # valores a serem interpolados, key possui uma lista respectiva de chaves
        # dos valores em keyValue, a fração a ser interpolada vem de set_fraction que varia de
        # zeroa a um. O campo keyValue deve conter exatamente tantas rotações 3D quanto os
        # quadros-chave no key.

        # O print abaixo é só para vocês verificarem o funcionamento, DEVE SER REMOVIDO.
        print("OrientationInterpolator : set_fraction = {0}".format(set_fraction))
        print("OrientationInterpolator : key = {0}".format(key)) # imprime no terminal
        print("OrientationInterpolator : keyValue = {0}".format(keyValue))

        # Abaixo está só um exemplo de como os dados podem ser calculados e transferidos
        value_changed = [0, 0, 1, 0]

        return value_changed

    # Para o futuro (Não para versão atual do projeto.)
    def vertex_shader(self, shader):
        """Para no futuro implementar um vertex shader."""

    def fragment_shader(self, shader):
        """Para no futuro implementar um fragment shader."""
